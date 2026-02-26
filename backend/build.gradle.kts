plugins {
    kotlin("jvm") version "2.0.21"
    application
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.ktor:ktor-server-core-jvm:2.3.12")
    implementation("io.ktor:ktor-server-netty-jvm:2.3.12")
    implementation("io.ktor:ktor-server-content-negotiation-jvm:2.3.12")
    implementation("io.ktor:ktor-serialization-kotlinx-json-jvm:2.3.12")
    implementation("org.jetbrains.exposed:exposed-core:0.53.0")
    implementation("org.jetbrains.exposed:exposed-jdbc:0.53.0")
    implementation("org.postgresql:postgresql:42.7.4")
    implementation("ch.qos.logback:logback-classic:1.5.8")

    testImplementation(kotlin("test"))
}

application {
    mainClass.set("com.neomelt.fmro.ApplicationKt")
}

tasks.test {
    useJUnitPlatform()
}

kotlin {
    jvmToolchain(17)
}
