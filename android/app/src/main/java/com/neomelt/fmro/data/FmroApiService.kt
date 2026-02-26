package com.neomelt.fmro.data

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface FmroApiService {
    @GET("api/v1/overview")
    suspend fun overview(): ApiOverview

    @GET("api/v1/companies")
    suspend fun companies(): List<ApiCompany>

    @GET("api/v1/jobs")
    suspend fun jobs(): List<ApiJobPosting>

    @GET("api/v1/applications")
    suspend fun applications(@Query("stage") stage: String? = null): List<ApiApplication>

    @POST("api/v1/applications")
    suspend fun createApplication(@Body request: ApiCreateApplicationRequest): ApiApplication

    @PUT("api/v1/applications/{id}")
    suspend fun updateApplication(
        @Path("id") id: Long,
        @Body request: ApiUpdateApplicationRequest,
    ): ApiApplication

    @POST("api/v1/crawler/run")
    suspend fun runCrawler(): ApiCrawlerRunResult

    @GET("api/v1/review-queue")
    suspend fun reviewQueue(@Query("status") status: String? = null): List<ApiReviewQueueItem>

    @POST("api/v1/review-queue/{id}/approve")
    suspend fun approveReview(@Path("id") id: Long): ApiJobPosting
}
