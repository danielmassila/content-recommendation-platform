package com.example.reco.auth;

import com.example.reco.model.UserRole;

public record AuthenticatedUser(Long id, String email, UserRole role) {
}
