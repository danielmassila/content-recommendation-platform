package com.example.reco.services;

import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.UpdateUserPreferencesRequest;
import com.example.reco.controllers.dto.UserPreferenceRequest;
import com.example.reco.controllers.dto.UserPreferenceResponse;
import com.example.reco.model.User;
import com.example.reco.model.UserPreference;
import com.example.reco.repositories.UserPreferenceRepository;
import com.example.reco.repositories.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
public class UserPreferenceServiceImpl implements UserPreferenceService {
    private final UserPreferenceRepository userPreferenceRepository;
    private final UserRepository userRepository;

    public UserPreferenceServiceImpl(UserPreferenceRepository userPreferenceRepository, UserRepository userRepository) {
        this.userPreferenceRepository = userPreferenceRepository;
        this.userRepository = userRepository;
    }

    @Override
    public List<UserPreferenceResponse> getUserPreferences(Long userId) {
        ensureUserExists(userId);

        return userPreferenceRepository.findByUserIdOrderByCreatedAtAsc(userId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Override
    @Transactional
    public List<UserPreferenceResponse> replaceUserPreferences(Long userId, UpdateUserPreferencesRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new NotFoundException("User with id " + userId + " not found"));
        Set<String> seenPreferences = new HashSet<>();

        userPreferenceRepository.deleteByUserId(userId);
        // Derived deletes are queued in the persistence context. Execute them
        // before inserting replacements so unchanged values do not violate the
        // database uniqueness constraint.
        userPreferenceRepository.flush();

        List<UserPreference> preferences = request.getEntries()
                .stream()
                .map(this::normalize)
                .filter(preference -> seenPreferences.add(preference.type().toLowerCase() + "::" + preference.value().toLowerCase()))
                .map(preference -> new UserPreference(user, preference.type(), preference.value()))
                .toList();

        return userPreferenceRepository.saveAll(preferences)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private void ensureUserExists(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new NotFoundException("User with id " + userId + " not found");
        }
    }

    private NormalizedPreference normalize(UserPreferenceRequest request) {
        return new NormalizedPreference(request.getType().trim(), request.getValue().trim());
    }

    private UserPreferenceResponse toResponse(UserPreference preference) {
        return new UserPreferenceResponse(
                preference.getId(),
                preference.getUser().getId(),
                preference.getType(),
                preference.getValue(),
                preference.getCreatedAt()
        );
    }

    private record NormalizedPreference(String type, String value) {
    }
}
