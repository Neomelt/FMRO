package com.neomelt.fmro.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ApiApplication(
    val id: Long,
    @SerialName("jobPostingId") val jobPostingId: Long? = null,
    @SerialName("companyName") val companyName: String,
    val role: String,
    @SerialName("appliedAt") val appliedAt: String? = null,
    @SerialName("deadlineAt") val deadlineAt: String? = null,
    val stage: String,
    val notes: String? = null,
    @SerialName("createdAt") val createdAt: String,
    @SerialName("updatedAt") val updatedAt: String,
)

@Serializable
data class ApiCreateApplicationRequest(
    @SerialName("jobPostingId") val jobPostingId: Long? = null,
    @SerialName("companyName") val companyName: String,
    val role: String,
    val stage: String = "Applied",
)

@Serializable
data class ApiUpdateApplicationRequest(
    val stage: String? = null,
)

@Serializable
data class ApiOverview(
    @SerialName("upcomingDeadlines") val upcomingDeadlines: Int,
    @SerialName("interviewsThisWeek") val interviewsThisWeek: Int,
    @SerialName("pendingReviews") val pendingReviews: Int,
)
