package com.example.reco.services;

import com.example.reco.controllers.dto.CreateUserRequest;
import com.example.reco.controllers.dto.UserResponse;

import java.util.List;

public interface UserService {
    UserResponse getUserById(Long id);

    List<UserResponse> getAllUsers(int limit);

    UserResponse createUser(CreateUserRequest request);
}
