package com.example.reco.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SecurityRateLimitFilterTest {

    @Test
    void limitsAuthenticationRequestsByRemoteAddress() throws Exception {
        SecurityRateLimitFilter filter = new SecurityRateLimitFilter(
                new ObjectMapper(),
                2,
                1,
                Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC)
        );

        assertEquals(200, executeLogin(filter).getStatus());
        assertEquals(200, executeLogin(filter).getStatus());

        MockHttpServletResponse rejected = executeLogin(filter);
        assertEquals(429, rejected.getStatus());
        assertEquals("60", rejected.getHeader("Retry-After"));
        assertTrue(rejected.getContentAsString().contains("RATE_LIMIT_EXCEEDED"));
    }

    private MockHttpServletResponse executeLogin(SecurityRateLimitFilter filter) throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/api/v1/auth/login");
        request.setRemoteAddr("192.0.2.10");
        MockHttpServletResponse response = new MockHttpServletResponse();
        filter.doFilter(request, response, new MockFilterChain());
        return response;
    }
}
