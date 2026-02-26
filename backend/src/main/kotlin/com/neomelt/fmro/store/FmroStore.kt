package com.neomelt.fmro.store

import com.neomelt.fmro.model.Company
import com.neomelt.fmro.model.CreateApplicationRequest
import com.neomelt.fmro.model.CreateCompanyRequest
import com.neomelt.fmro.model.CreateInterviewRoundRequest
import com.neomelt.fmro.model.CreateJobPostingRequest
import com.neomelt.fmro.model.CreateReviewQueueRequest
import com.neomelt.fmro.model.CrawlRunResult
import com.neomelt.fmro.model.InterviewRound
import com.neomelt.fmro.model.JobApplication
import com.neomelt.fmro.model.JobPosting
import com.neomelt.fmro.model.Overview
import com.neomelt.fmro.model.ReviewQueueItem
import com.neomelt.fmro.model.UpdateApplicationRequest
import com.neomelt.fmro.model.UpdateCompanyRequest
import com.neomelt.fmro.model.UpdateInterviewRoundRequest
import com.neomelt.fmro.model.UpdateJobPostingRequest

interface FmroStore {
    fun listCompanies(): List<Company>
    fun createCompany(req: CreateCompanyRequest): Company
    fun updateCompany(id: Long, req: UpdateCompanyRequest): Company?
    fun deleteCompany(id: Long): Boolean

    fun listJobs(companyId: Long?): List<JobPosting>
    fun createJob(req: CreateJobPostingRequest): JobPosting
    fun updateJob(id: Long, req: UpdateJobPostingRequest): JobPosting?
    fun deleteJob(id: Long): Boolean

    fun listApplications(stage: String?): List<JobApplication>
    fun createApplication(req: CreateApplicationRequest): JobApplication
    fun updateApplication(id: Long, req: UpdateApplicationRequest): JobApplication?
    fun deleteApplication(id: Long): Boolean

    fun listRounds(applicationId: Long): List<InterviewRound>
    fun createRound(applicationId: Long, req: CreateInterviewRoundRequest): InterviewRound
    fun updateRound(id: Long, req: UpdateInterviewRoundRequest): InterviewRound?
    fun deleteRound(id: Long): Boolean

    fun listReviewQueue(status: String?): List<ReviewQueueItem>
    fun createReview(req: CreateReviewQueueRequest): ReviewQueueItem
    fun approveReview(id: Long): JobPosting
    fun rejectReview(id: Long): ReviewQueueItem

    fun runCrawler(): CrawlRunResult
    fun overview(): Overview
}
