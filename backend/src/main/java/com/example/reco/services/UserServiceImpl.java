package com.example.reco.services;

import com.example.reco.common.exceptions.BadRequestException;
import com.example.reco.common.exceptions.ConflictException;
import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.ChangePasswordRequest;
import com.example.reco.controllers.dto.CreateUserRequest;
import com.example.reco.controllers.dto.UpdateUserRequest;
import com.example.reco.controllers.dto.UserResponse;
import com.example.reco.model.User;
import com.example.reco.repositories.UserRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class UserServiceImpl implements UserService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserServiceImpl(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    @Transactional(readOnly = true)
    public UserResponse getUserById(Long id) {
        User user = userRepository.findById(id).orElseThrow(() -> new NotFoundException("User with id " + id + " not found"));
        return toResponse(user);
    }

    @Override
    @Transactional(readOnly = true)
    public List<UserResponse> getAllUsers(int limit) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        List<UserResponse> userList = userRepository
                                              .findAll(PageRequest.of(0, myLimit))
                                              .stream()
                                              .map(this::toResponse)
                                              .toList();
        return userList;
    }

    @Override
    public UserResponse createUser(CreateUserRequest request) {
        String email = request.getEmail();
        if (userRepository.existsByEmail(email)) {
            throw new ConflictException("Email already taken: " + email);
        }
        User user = new User();
        user.setEmail(email);
        // TO DO : add a password that we directly hash
        User saved = userRepository.save(user);
        return toResponse(saved);
    }

    @Override
    public UserResponse updateUser(Long id, UpdateUserRequest request) {
        User user = userRepository.findById(id).orElseThrow(() -> new NotFoundException("User with id " + id + " not found"));
        String email = request.getEmail().trim().toLowerCase();
        String username = request.getUsername().trim();

        if (userRepository.existsByEmailAndIdNot(email, id)) {
            throw new ConflictException("Email already taken: " + email);
        }

        if (userRepository.existsByUsernameAndIdNot(username, id)) {
            throw new ConflictException("Username already taken: " + username);
        }

        user.setEmail(email);
        user.setUsername(username);
        return toResponse(userRepository.save(user));
    }

    @Override
    public void changePassword(Long id, ChangePasswordRequest request) {
        User user = userRepository.findById(id).orElseThrow(() -> new NotFoundException("User with id " + id + " not found"));

        if (user.getPasswordHash() == null || !passwordEncoder.matches(request.getCurrentPassword(), user.getPasswordHash())) {
            throw new BadRequestException("Current password is invalid");
        }

        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);
    }

    private UserResponse toResponse(User user) {
        return new UserResponse(
                user.getId(),
                user.getEmail(),
                user.getUsername()
        );
    }

}
