package com.example.reco.auth;

import com.example.reco.model.User;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;

@Service
public class JwtService {

    private static final String HMAC_ALGORITHM = "HmacSHA256";
    private static final Base64.Encoder BASE64_URL_ENCODER = Base64.getUrlEncoder().withoutPadding();
    private static final Base64.Decoder BASE64_URL_DECODER = Base64.getUrlDecoder();
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ObjectMapper objectMapper;
    private final Clock clock;
    private final String secret;
    private final long expirationSeconds;

    public JwtService(
            ObjectMapper objectMapper,
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration-seconds:86400}") long expirationSeconds
    ) {
        this.objectMapper = objectMapper;
        this.clock = Clock.systemUTC();
        this.secret = secret;
        this.expirationSeconds = expirationSeconds;
    }

    public String createToken(User user) {
        Instant now = Instant.now(clock);
        Map<String, Object> header = Map.of(
                "alg", "HS256",
                "typ", "JWT"
        );
        Map<String, Object> payload = Map.of(
                "sub", user.getEmail(),
                "userId", user.getId(),
                "iat", now.getEpochSecond(),
                "exp", now.plusSeconds(expirationSeconds).getEpochSecond()
        );

        String unsignedToken = encodeJson(header) + "." + encodeJson(payload);
        return unsignedToken + "." + sign(unsignedToken);
    }

    public JwtClaims validateToken(String token) {
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            throw new IllegalArgumentException("Invalid token");
        }

        String unsignedToken = parts[0] + "." + parts[1];
        String expectedSignature = sign(unsignedToken);
        if (!MessageDigest.isEqual(expectedSignature.getBytes(StandardCharsets.UTF_8), parts[2].getBytes(StandardCharsets.UTF_8))) {
            throw new IllegalArgumentException("Invalid token signature");
        }

        Map<String, Object> claims = decodeJson(parts[1]);
        long expiresAt = readLong(claims.get("exp"));
        if (Instant.now(clock).getEpochSecond() >= expiresAt) {
            throw new IllegalArgumentException("Expired token");
        }

        Long userId = readLong(claims.get("userId"));
        String email = String.valueOf(claims.get("sub"));
        return new JwtClaims(userId, email);
    }

    private String encodeJson(Map<String, Object> value) {
        try {
            return BASE64_URL_ENCODER.encodeToString(objectMapper.writeValueAsBytes(value));
        } catch (Exception exception) {
            throw new IllegalStateException("Could not encode JWT", exception);
        }
    }

    private Map<String, Object> decodeJson(String value) {
        try {
            byte[] decoded = BASE64_URL_DECODER.decode(value);
            return objectMapper.readValue(decoded, MAP_TYPE);
        } catch (Exception exception) {
            throw new IllegalArgumentException("Invalid token payload", exception);
        }
    }

    private String sign(String value) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALGORITHM);
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), HMAC_ALGORITHM));
            return BASE64_URL_ENCODER.encodeToString(mac.doFinal(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("Could not sign JWT", exception);
        }
    }

    private long readLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }

        return Long.parseLong(String.valueOf(value));
    }
}
