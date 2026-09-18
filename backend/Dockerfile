FROM maven:3.9-eclipse-temurin-21 AS BUILD

WORKDIR /app
COPY pom.xml .
COPY src ./src

RUN mvn clean package

FROM eclipse-temurin:21-jre

WORKDIR /app
COPY --from=BUILD /app/target/*.jar app.jar

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "app.jar"]
