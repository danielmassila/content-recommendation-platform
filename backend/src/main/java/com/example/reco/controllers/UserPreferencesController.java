package com.example.reco.controllers;

import com.example.reco.controllers.dto.UpdateUserPreferencesRequest;
import com.example.reco.controllers.dto.UserPreferenceResponse;
import com.example.reco.services.UserPreferenceService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/users/{userId}/preferences")
public class UserPreferencesController {
    private final UserPreferenceService userPreferenceService;

    public UserPreferencesController(UserPreferenceService userPreferenceService) {
        this.userPreferenceService = userPreferenceService;
    }

    @GetMapping
    public List<UserPreferenceResponse> getUserPreferences(@PathVariable Long userId) {
        return userPreferenceService.getUserPreferences(userId);
    }

    @PutMapping
    public List<UserPreferenceResponse> replaceUserPreferences(
            @PathVariable Long userId,
            @Valid @RequestBody UpdateUserPreferencesRequest request
    ) {
        return userPreferenceService.replaceUserPreferences(userId, request);
    }
}
