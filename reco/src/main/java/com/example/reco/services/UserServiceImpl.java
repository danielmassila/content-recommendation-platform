package com.example.reco.services;

import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.CreateUserRequest;
import com.example.reco.controllers.dto.UserResponse;
import com.example.reco.model.User;
import com.example.reco.repositories.UserRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class UserServiceImpl implements UserService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;

    private UserRepository userRepository;

    public UserServiceImpl(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public UserResponse getUserById(Long id) {
        User user = userRepository.findById(id).orElseThrow(() -> new NotFoundException("User with id " + id + " not found"));
        return toResponse(user);
    }

    @Override
    @Transactional(readOnly = true)
    public List<UserResponse> getAllUsers(int limit) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        List<UserResponse> userList = userRepository
                                              .findAll(PageRequest.of(0, myLimit))
                                              .stream()
                                              .map(this::toResponse)
                                              .toList();
        return userList;
    }

    @Override
    public UserResponse createUser(CreateUserRequest request) {
        User user = new User();
        user.setEmail(request.getEmail());
        // TO DO : add a password that we directly hash
        User saved = userRepository.save(user);
        return toResponse(saved);
    }

    private UserResponse toResponse(User user) {
        return new UserResponse(
                user.getId(),
                user.getEmail()
        );
    }

}
