package com.neomelt.fmro.model

import kotlinx.serialization.Serializable

@Serializable
data class Company(
    val id: Long,
    val name: String,
    val officialSite: String? = null,
    val careersUrl: String? = null,
    val active: Boolean = true,
    val createdAt: String,
    val updatedAt: String,
)

@Serializable
data class CreateCompanyRequest(
    val name: String,
    val officialSite: String? = null,
    val careersUrl: String? = null,
    val active: Boolean = true,
)

@Serializable
data class UpdateCompanyRequest(
    val name: String? = null,
    val officialSite: String? = null,
    val careersUrl: String? = null,
    val active: Boolean? = null,
)

@Serializable
data class JobPosting(
    val id: Long,
    val companyId: Long,
    val title: String,
    val location: String? = null,
    val sourceUrl: String? = null,
    val applyUrl: String? = null,
    val deadlineAt: String? = null,
    val status: String = "open",
    val firstSeenAt: String,
    val lastSeenAt: String,
)

@Serializable
data class CreateJobPostingRequest(
    val companyId: Long,
    val title: String,
    val location: String? = null,
    val sourceUrl: String? = null,
    val applyUrl: String? = null,
    val deadlineAt: String? = null,
    val status: String = "open",
)

@Serializable
data class UpdateJobPostingRequest(
    val title: String? = null,
    val location: String? = null,
    val sourceUrl: String? = null,
    val applyUrl: String? = null,
    val deadlineAt: String? = null,
    val status: String? = null,
)

@Serializable
data class JobApplication(
    val id: Long,
    val jobPostingId: Long? = null,
    val companyName: String,
    val role: String,
    val appliedAt: String? = null,
    val deadlineAt: String? = null,
    val stage: String = "applied",
    val notes: String? = null,
    val createdAt: String,
    val updatedAt: String,
)

@Serializable
data class CreateApplicationRequest(
    val jobPostingId: Long? = null,
    val companyName: String,
    val role: String,
    val appliedAt: String? = null,
    val deadlineAt: String? = null,
    val stage: String = "applied",
    val notes: String? = null,
)

@Serializable
data class UpdateApplicationRequest(
    val companyName: String? = null,
    val role: String? = null,
    val appliedAt: String? = null,
    val deadlineAt: String? = null,
    val stage: String? = null,
    val notes: String? = null,
)

@Serializable
data class InterviewRound(
    val id: Long,
    val applicationId: Long,
    val roundNo: Int,
    val scheduledAt: String? = null,
    val outcome: String? = null,
    val note: String? = null,
    val createdAt: String,
)

@Serializable
data class CreateInterviewRoundRequest(
    val roundNo: Int,
    val scheduledAt: String? = null,
    val outcome: String? = null,
    val note: String? = null,
)

@Serializable
data class UpdateInterviewRoundRequest(
    val roundNo: Int? = null,
    val scheduledAt: String? = null,
    val outcome: String? = null,
    val note: String? = null,
)

@Serializable
data class Overview(
    val upcomingDeadlines: Int,
    val interviewsThisWeek: Int,
    val pendingReviews: Int,
)

@Serializable
data class ErrorResponse(
    val message: String,
)

@Serializable
data class ReviewQueueItem(
    val id: Long,
    val sourceType: String,
    val payload: Map<String, String>,
    val confidence: Double? = null,
    val status: String = "pending",
    val createdAt: String,
    val reviewedAt: String? = null,
)

@Serializable
data class CreateReviewQueueRequest(
    val sourceType: String,
    val payload: Map<String, String>,
    val confidence: Double? = null,
)

@Serializable
data class CrawlRunResult(
    val scannedCompanies: Int,
    val queuedItems: Int,
)
