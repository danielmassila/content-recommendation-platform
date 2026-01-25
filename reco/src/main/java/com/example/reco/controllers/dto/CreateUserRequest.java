package com.example.reco.controllers.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class CreateUserRequest {
    @NotBlank(message = "email is required")
    @Size(min = 4, max = 30, message = "email must be between 4 and 30 characters")
    private String email;

    public CreateUserRequest() {
    }

    public CreateUserRequest(String email) {
        this.email = email;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
