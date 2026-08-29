package com.example.reco.services;

import com.example.reco.controllers.dto.UpdateUserPreferencesRequest;
import com.example.reco.controllers.dto.UserPreferenceResponse;

import java.util.List;

public interface UserPreferenceService {
    List<UserPreferenceResponse> getUserPreferences(Long userId);

    List<UserPreferenceResponse> replaceUserPreferences(Long userId, UpdateUserPreferencesRequest request);
}
