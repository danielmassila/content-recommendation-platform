package com.example.reco.services;

import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.common.exceptions.RecommendationJobException;
import com.example.reco.model.Recommendation;
import com.example.reco.repositories.RecommendationRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;

@Service
@Transactional
public class RecommendationServiceImpl implements RecommendationService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;

    private final RecommendationRepository recommendationRepository;

    @Value("${app.recommendations.job-timeout-seconds:120}")
    private long jobTimeoutSeconds;

    @Value("${app.recommendations.compose-file:../docker-compose.yml}")
    private String composeFile;

    public RecommendationServiceImpl(RecommendationRepository recommendationRepository) {
        this.recommendationRepository = recommendationRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public List<RecommendationResponse> getAllRecommendations(int limit, boolean includeReason) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        List<RecommendationResponse> recommendationList = recommendationRepository.findAll(PageRequest.of(0, myLimit))
                                                                  .stream()
                                                                  .map(r -> toResponse(r, true))
                                                                  .toList();
        return recommendationList;
    }

    @Override
    @Transactional(readOnly = true)
    public List<RecommendationResponse> getUserRecommendations(Long userId, int limit, boolean includeReason, String algo) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);

        List<Recommendation> recommendations;
        PageRequest page = PageRequest.of(0, myLimit);

        if (algo != null && !algo.isBlank()) {
            recommendations = recommendationRepository
                                      .findByUserIdAndAlgoVersion(userId, algo, page)
                                      .getContent();
        } else {
            recommendations = recommendationRepository
                                      .findByUserId(userId, page)
                                      .getContent();
        }

        return recommendations.stream()
                       .map(r -> toResponse(r, includeReason))
                       .toList();

    }

    @Override
    public List<RecommendationResponse> recomputeRecommendationsForUser(Long userId, int limit, boolean includeReason, String algo) {
        runRecommendationJob("user:" + userId);
        return getUserRecommendations(userId, limit, includeReason, algo);
    }

    @Override
    public void recomputeAllRecommendations() {
        runRecommendationJob("all");
    }

    @Override
    public void runRecommendationJob(String mode) {
        try {
            ProcessBuilder pb = createProcessBuilder(mode);
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.INHERIT);

            Process p = startProcess(pb);

            long timeout = jobTimeoutSeconds > 0 ? jobTimeoutSeconds : 120;
            if (!p.waitFor(timeout, TimeUnit.SECONDS)) {
                p.destroyForcibly();
                throw new RecommendationJobException("Recommendation computation timed out");
            }

            int exit = p.exitValue();

            if (exit != 0) {
                throw new RecommendationJobException("Recommendation computation failed with exit code " + exit);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RecommendationJobException("Recommendation computation interrupted", e);
        } catch (RecommendationJobException e) {
            throw e;
        } catch (Exception e) {
            throw new RecommendationJobException("Unable to start recommendation computation", e);
        }
    }

    // testables hooks
    protected ProcessBuilder createProcessBuilder(String mode) {
        List<String> command = new ArrayList<>(List.of(
                "docker", "compose", "-f",
                composeFile == null || composeFile.isBlank() ? "../docker-compose.yml" : composeFile,
                "run", "--rm",
                "reco-job",
                "python", "-m", "jobs.run_reco",
                "--n", "20",
                "--k", "50",
                "--algo", "hybrid_usercf_pop"
        ));
        if (mode.startsWith("user:")) {
            command.add("--user-id");
            command.add(mode.substring("user:".length()));
        }
        return new ProcessBuilder(command);
    }

    protected Process startProcess(ProcessBuilder pb) throws Exception {
        return pb.start();
    }

    private RecommendationResponse toResponse(Recommendation recommendation, boolean includeReason) {
        return new RecommendationResponse(
                recommendation.getId(),
                recommendation.getUser().getId(),
                recommendation.getItem().getId(),
                recommendation.getScore(),
                recommendation.getRank(),
                recommendation.getAlgoVersion(),
                recommendation.getRunId(),
                includeReason ? recommendation.getReason() : null,
                recommendation.getGeneratedAt(),
                new ItemResponse(
                        recommendation.getItem().getId(),
                        recommendation.getItem().getTitle(),
                        recommendation.getItem().getType(),
                        recommendation.getItem().getMetadata()
                )
        );
    }

}
