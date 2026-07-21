package com.example.reco.controllers.dto;

public class AuthResponse {

    private final String accessToken;
    private final UserResponse user;

    public AuthResponse(String accessToken, UserResponse user) {
        this.accessToken = accessToken;
        this.user = user;
    }

    public String getAccessToken() {
        return accessToken;
    }

    public UserResponse getUser() {
        return user;
    }
}
