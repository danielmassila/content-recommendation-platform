package com.example.reco.controllers.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class UpdateUserRequest {
    @Email(message = "email must be valid")
    @NotBlank(message = "email is required")
    @Size(max = 120, message = "email must be at most 120 characters")
    private String email;

    @NotBlank(message = "username is required")
    @Size(min = 2, max = 80, message = "username must be between 2 and 80 characters")
    private String username;

    public String getEmail() {
        return email;
    }

    public String getUsername() {
        return username;
    }
}
