package com.example.reco.controllers.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RegisterRequest {

    @Email(message = "email must be valid")
    @NotBlank(message = "email is required")
    @Size(max = 120, message = "email must be at most 120 characters")
    private String email;

    @NotBlank(message = "password is required")
    @Size(min = 8, max = 120, message = "password must be between 8 and 120 characters")
    private String password;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }
}
