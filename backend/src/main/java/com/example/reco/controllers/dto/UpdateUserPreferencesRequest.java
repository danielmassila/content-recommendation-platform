package com.example.reco.controllers.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.util.ArrayList;
import java.util.List;

public class UpdateUserPreferencesRequest {
    @NotNull
    @Valid
    private List<UserPreferenceRequest> entries = new ArrayList<>();

    public UpdateUserPreferencesRequest() {
    }

    public UpdateUserPreferencesRequest(List<UserPreferenceRequest> entries) {
        this.entries = entries;
    }

    public List<UserPreferenceRequest> getEntries() {
        return entries;
    }
}
