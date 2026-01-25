package com.example.reco.controllers.dto;

public class UserResponse {
    private Long id;
    private String email;

    public UserResponse(Long id, String username) {
        this.id = id;
        this.email = username;
    }

    public Long getId() {
        return id;
    }

    public String getEmail() {
        return email;
    }
}
