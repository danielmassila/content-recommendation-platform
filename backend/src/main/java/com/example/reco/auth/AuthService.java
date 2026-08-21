package com.example.reco.auth;

import com.example.reco.common.exceptions.BadRequestException;
import com.example.reco.common.exceptions.ConflictException;
import com.example.reco.common.exceptions.UnauthorizedException;
import com.example.reco.controllers.dto.AuthRequest;
import com.example.reco.controllers.dto.AuthResponse;
import com.example.reco.controllers.dto.RegisterRequest;
import com.example.reco.controllers.dto.UserResponse;
import com.example.reco.model.User;
import com.example.reco.repositories.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    public AuthResponse register(RegisterRequest request) {
        String email = normalizeEmail(request.getEmail());
        String username = normalizeUsername(request.getUsername());
        if (userRepository.existsByEmail(email)) {
            throw new ConflictException("Email already taken: " + email);
        }

        if (userRepository.existsByUsername(username)) {
            throw new ConflictException("Username already taken: " + username);
        }

        User user = new User(email, username, passwordEncoder.encode(request.getPassword()));
        User savedUser = userRepository.save(user);
        return toAuthResponse(savedUser);
    }

    @Transactional(readOnly = true)
    public AuthResponse login(AuthRequest request) {
        String email = normalizeEmail(request.getEmail());
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UnauthorizedException("Invalid email or password"));

        if (user.getPasswordHash() == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new UnauthorizedException("Invalid email or password");
        }

        return toAuthResponse(user);
    }

    public UserResponse toUserResponse(AuthenticatedUser user) {
        User loadedUser = userRepository.findById(user.id())
                .orElseThrow(() -> new BadRequestException("Authenticated user not found"));
        return toUserResponse(loadedUser);
    }

    private AuthResponse toAuthResponse(User user) {
        return new AuthResponse(
                jwtService.createToken(user),
                toUserResponse(user)
        );
    }

    private UserResponse toUserResponse(User user) {
        return new UserResponse(user.getId(), user.getEmail(), user.getUsername(), user.getRole());
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase();
    }

    private String normalizeUsername(String username) {
        return username.trim();
    }
}
