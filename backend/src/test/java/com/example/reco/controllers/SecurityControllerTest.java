package com.example.reco.controllers;

import com.example.reco.auth.AuthenticatedUser;
import com.example.reco.auth.JwtService;
import com.example.reco.auth.JwtAuthenticationFilter;
import com.example.reco.auth.SecurityRateLimitFilter;
import com.example.reco.config.SecurityConfig;
import com.example.reco.controllers.dto.RatingResponse;
import com.example.reco.controllers.dto.UserResponse;
import com.example.reco.model.UserRole;
import com.example.reco.repositories.UserRepository;
import com.example.reco.services.RatingService;
import com.example.reco.services.RecommendationService;
import com.example.reco.services.UserPreferenceService;
import com.example.reco.services.UserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.authentication;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest({MeController.class, RecommendationsController.class})
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityRateLimitFilter.class})
class SecurityControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private UserService userService;
    @MockitoBean
    private RatingService ratingService;
    @MockitoBean
    private UserPreferenceService userPreferenceService;
    @MockitoBean
    private RecommendationService recommendationService;
    @MockitoBean
    private JwtService jwtService;
    @MockitoBean
    private UserRepository userRepository;

    @Test
    void rejectsAnonymousAccessWithProblemDetail() throws Exception {
        mockMvc.perform(get("/api/v1/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("AUTHENTICATION_REQUIRED"));
    }

    @Test
    void rejectsStandardUserFromAdminEndpoint() throws Exception {
        AuthenticatedUser principal = new AuthenticatedUser(7L, "user@example.com", UserRole.USER);

        mockMvc.perform(get("/api/v1/admin/recommendations")
                        .with(authenticated(principal)))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("ACCESS_DENIED"));
    }

    @Test
    void allowsAdminOnAdminEndpoint() throws Exception {
        AuthenticatedUser principal = new AuthenticatedUser(1L, "admin@example.com", UserRole.ADMIN);
        when(recommendationService.getAllRecommendations(anyInt(), anyBoolean())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/admin/recommendations")
                        .with(authenticated(principal)))
                .andExpect(status().isOk());
    }

    @Test
    void meProfileUsesAuthenticatedIdentity() throws Exception {
        AuthenticatedUser principal = new AuthenticatedUser(7L, "user@example.com", UserRole.USER);
        when(userService.getUserById(7L))
                .thenReturn(new UserResponse(7L, "user@example.com", "user", UserRole.USER));

        mockMvc.perform(get("/api/v1/me").with(authenticated(principal)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(7));

        verify(userService).getUserById(7L);
    }

    @Test
    void ratingUsesAuthenticatedIdentityInsteadOfRequestBodyUserId() throws Exception {
        AuthenticatedUser principal = new AuthenticatedUser(7L, "user@example.com", UserRole.USER);
        when(ratingService.rateItem(99L, 7L, BigDecimal.valueOf(4)))
                .thenReturn(new RatingResponse(1L, 7L, 99L, BigDecimal.valueOf(4), Instant.now()));

        mockMvc.perform(put("/api/v1/me/ratings/99")
                        .with(authenticated(principal))
                        .contentType("application/json")
                        .content("{\"grade\":4,\"userId\":42}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(7));

        verify(ratingService).rateItem(99L, 7L, BigDecimal.valueOf(4));
    }

    private RequestPostProcessor authenticated(AuthenticatedUser principal) {
        return authentication(new UsernamePasswordAuthenticationToken(
                principal,
                null,
                List.of(new SimpleGrantedAuthority("ROLE_" + principal.role().name()))
        ));
    }
}
