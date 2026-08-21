package com.example.reco.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Clock;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class SecurityRateLimitFilter extends OncePerRequestFilter {

    private static final long WINDOW_MILLIS = 60_000L;

    private final ObjectMapper objectMapper;
    private final int authenticationLimit;
    private final int recomputeLimit;
    private final Clock clock;
    private final ConcurrentHashMap<String, WindowCounter> counters = new ConcurrentHashMap<>();
    private final AtomicLong requestCounter = new AtomicLong();

    @Autowired
    public SecurityRateLimitFilter(
            ObjectMapper objectMapper,
            @Value("${app.rate-limit.authentication-per-minute:10}") int authenticationLimit,
            @Value("${app.rate-limit.recompute-per-minute:3}") int recomputeLimit
    ) {
        this(objectMapper, authenticationLimit, recomputeLimit, Clock.systemUTC());
    }

    SecurityRateLimitFilter(ObjectMapper objectMapper, int authenticationLimit, int recomputeLimit, Clock clock) {
        this.objectMapper = objectMapper;
        this.authenticationLimit = authenticationLimit;
        this.recomputeLimit = recomputeLimit;
        this.clock = clock;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        LimitRule rule = resolveRule(request);
        if (rule == null) {
            filterChain.doFilter(request, response);
            return;
        }

        long currentWindow = clock.millis() / WINDOW_MILLIS;
        String key = rule.name() + ':' + request.getRemoteAddr();
        WindowCounter counter = counters.compute(key, (ignored, existing) -> {
            if (existing == null || existing.window() != currentWindow) {
                return new WindowCounter(currentWindow, 1);
            }
            return new WindowCounter(currentWindow, existing.count() + 1);
        });

        if ((requestCounter.incrementAndGet() & 1023) == 0) {
            counters.entrySet().removeIf(entry -> entry.getValue().window() < currentWindow - 1);
        }

        if (counter.count() > rule.limit()) {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);
            response.setHeader("Retry-After", "60");
            ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                    HttpStatus.TOO_MANY_REQUESTS,
                    "Too many requests. Try again later."
            );
            problem.setTitle("Too many requests");
            problem.setProperty("code", "RATE_LIMIT_EXCEEDED");
            objectMapper.writeValue(response.getOutputStream(), problem);
            return;
        }

        filterChain.doFilter(request, response);
    }

    private LimitRule resolveRule(HttpServletRequest request) {
        if (!"POST".equals(request.getMethod())) {
            return null;
        }

        String path = request.getRequestURI();
        if (path.equals("/api/v1/auth/login") || path.equals("/api/v1/auth/register")) {
            return new LimitRule("authentication", authenticationLimit);
        }
        if (path.endsWith("/recommendations/recompute")) {
            return new LimitRule("recompute", recomputeLimit);
        }
        return null;
    }

    private record LimitRule(String name, int limit) {
    }

    private record WindowCounter(long window, int count) {
    }
}
