package com.example.reco.controllers.dto;

import com.example.reco.model.UserRole;

public class UserResponse {
    private Long id;
    private String email;
    private String username;
    private UserRole role;

    public UserResponse(Long id, String email, String username, UserRole role) {
        this.id = id;
        this.email = email;
        this.username = username;
        this.role = role;
    }

    public Long getId() {
        return id;
    }

    public String getEmail() {
        return email;
    }

    public String getUsername() {
        return username;
    }

    public UserRole getRole() {
        return role;
    }
}
