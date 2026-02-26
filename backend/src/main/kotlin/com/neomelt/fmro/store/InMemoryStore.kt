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
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration
import java.time.Instant
import java.time.ZoneOffset
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

object InMemoryStore : FmroStore {
    private val companySeq = AtomicLong(0)
    private val jobSeq = AtomicLong(0)
    private val applicationSeq = AtomicLong(0)
    private val roundSeq = AtomicLong(0)
    private val reviewSeq = AtomicLong(0)

    private val companies = ConcurrentHashMap<Long, Company>()
    private val jobs = ConcurrentHashMap<Long, JobPosting>()
    private val applications = ConcurrentHashMap<Long, JobApplication>()
    private val rounds = ConcurrentHashMap<Long, InterviewRound>()
    private val reviews = ConcurrentHashMap<Long, ReviewQueueItem>()

    private val httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .followRedirects(HttpClient.Redirect.NORMAL)
        .build()

    private val titleRegex = Regex("(?is)<title[^>]*>(.*?)</title>")

    private fun nowIso(): String = Instant.now().toString()

    override fun listCompanies(): List<Company> = companies.values.sortedBy { it.id }

    override fun createCompany(req: CreateCompanyRequest): Company {
        val id = companySeq.incrementAndGet()
        val now = nowIso()
        val company = Company(
            id = id,
            name = req.name.trim(),
            officialSite = req.officialSite,
            careersUrl = req.careersUrl,
            active = req.active,
            createdAt = now,
            updatedAt = now,
        )
        companies[id] = company
        return company
    }

    override fun updateCompany(id: Long, req: UpdateCompanyRequest): Company? {
        val current = companies[id] ?: return null
        val updated = current.copy(
            name = req.name?.trim() ?: current.name,
            officialSite = req.officialSite ?: current.officialSite,
            careersUrl = req.careersUrl ?: current.careersUrl,
            active = req.active ?: current.active,
            updatedAt = nowIso(),
        )
        companies[id] = updated
        return updated
    }

    override fun deleteCompany(id: Long): Boolean {
        val deleted = companies.remove(id) ?: return false
        val companyJobs = jobs.values.filter { it.companyId == deleted.id }.map { it.id }
        companyJobs.forEach { deleteJob(it) }
        return true
    }

    override fun listJobs(companyId: Long?): List<JobPosting> = jobs.values
        .asSequence()
        .filter { companyId == null || it.companyId == companyId }
        .sortedBy { it.id }
        .toList()

    override fun createJob(req: CreateJobPostingRequest): JobPosting {
        require(companies.containsKey(req.companyId)) { "companyId ${req.companyId} does not exist" }
        val id = jobSeq.incrementAndGet()
        val now = nowIso()
        val posting = JobPosting(
            id = id,
            companyId = req.companyId,
            title = req.title.trim(),
            location = req.location,
            sourceUrl = req.sourceUrl,
            applyUrl = req.applyUrl,
            deadlineAt = req.deadlineAt,
            status = req.status,
            firstSeenAt = now,
            lastSeenAt = now,
        )
        jobs[id] = posting
        return posting
    }

    override fun updateJob(id: Long, req: UpdateJobPostingRequest): JobPosting? {
        val current = jobs[id] ?: return null
        val updated = current.copy(
            title = req.title?.trim() ?: current.title,
            location = req.location ?: current.location,
            sourceUrl = req.sourceUrl ?: current.sourceUrl,
            applyUrl = req.applyUrl ?: current.applyUrl,
            deadlineAt = req.deadlineAt ?: current.deadlineAt,
            status = req.status ?: current.status,
            lastSeenAt = nowIso(),
        )
        jobs[id] = updated
        return updated
    }

    override fun deleteJob(id: Long): Boolean {
        if (jobs.remove(id) == null) return false
        applications.values
            .filter { it.jobPostingId == id }
            .forEach { app -> applications[app.id] = app.copy(jobPostingId = null, updatedAt = nowIso()) }
        return true
    }

    override fun listApplications(stage: String?): List<JobApplication> = applications.values
        .asSequence()
        .filter { stage == null || it.stage.equals(stage, ignoreCase = true) }
        .sortedBy { it.id }
        .toList()

    override fun createApplication(req: CreateApplicationRequest): JobApplication {
        if (req.jobPostingId != null) {
            require(jobs.containsKey(req.jobPostingId)) { "jobPostingId ${req.jobPostingId} does not exist" }
        }
        val id = applicationSeq.incrementAndGet()
        val now = nowIso()
        val app = JobApplication(
            id = id,
            jobPostingId = req.jobPostingId,
            companyName = req.companyName.trim(),
            role = req.role.trim(),
            appliedAt = req.appliedAt,
            deadlineAt = req.deadlineAt,
            stage = req.stage,
            notes = req.notes,
            createdAt = now,
            updatedAt = now,
        )
        applications[id] = app
        return app
    }

    override fun updateApplication(id: Long, req: UpdateApplicationRequest): JobApplication? {
        val current = applications[id] ?: return null
        val updated = current.copy(
            companyName = req.companyName?.trim() ?: current.companyName,
            role = req.role?.trim() ?: current.role,
            appliedAt = req.appliedAt ?: current.appliedAt,
            deadlineAt = req.deadlineAt ?: current.deadlineAt,
            stage = req.stage ?: current.stage,
            notes = req.notes ?: current.notes,
            updatedAt = nowIso(),
        )
        applications[id] = updated
        return updated
    }

    override fun deleteApplication(id: Long): Boolean {
        if (applications.remove(id) == null) return false
        rounds.values.filter { it.applicationId == id }.forEach { rounds.remove(it.id) }
        return true
    }

    override fun listRounds(applicationId: Long): List<InterviewRound> = rounds.values
        .asSequence()
        .filter { it.applicationId == applicationId }
        .sortedBy { it.roundNo }
        .toList()

    override fun createRound(applicationId: Long, req: CreateInterviewRoundRequest): InterviewRound {
        require(applications.containsKey(applicationId)) { "applicationId $applicationId does not exist" }
        val id = roundSeq.incrementAndGet()
        val round = InterviewRound(
            id = id,
            applicationId = applicationId,
            roundNo = req.roundNo,
            scheduledAt = req.scheduledAt,
            outcome = req.outcome,
            note = req.note,
            createdAt = nowIso(),
        )
        rounds[id] = round
        return round
    }

    override fun updateRound(id: Long, req: UpdateInterviewRoundRequest): InterviewRound? {
        val current = rounds[id] ?: return null
        val updated = current.copy(
            roundNo = req.roundNo ?: current.roundNo,
            scheduledAt = req.scheduledAt ?: current.scheduledAt,
            outcome = req.outcome ?: current.outcome,
            note = req.note ?: current.note,
        )
        rounds[id] = updated
        return updated
    }

    override fun deleteRound(id: Long): Boolean = rounds.remove(id) != null

    override fun listReviewQueue(status: String?): List<ReviewQueueItem> = reviews.values
        .asSequence()
        .filter { status == null || it.status.equals(status, ignoreCase = true) }
        .sortedByDescending { it.id }
        .toList()

    override fun createReview(req: CreateReviewQueueRequest): ReviewQueueItem {
        val id = reviewSeq.incrementAndGet()
        val item = ReviewQueueItem(
            id = id,
            sourceType = req.sourceType,
            payload = req.payload,
            confidence = req.confidence,
            status = "pending",
            createdAt = nowIso(),
            reviewedAt = null,
        )
        reviews[id] = item
        return item
    }

    override fun approveReview(id: Long): JobPosting {
        val current = reviews[id] ?: error("review $id not found")
        require(current.status == "pending") { "review $id is already ${current.status}" }

        val companyId = current.payload["companyId"]?.toLongOrNull()
            ?: error("review $id missing valid companyId")
        val title = current.payload["title"]?.takeIf { it.isNotBlank() }
            ?: error("review $id missing title")

        val created = createJob(
            CreateJobPostingRequest(
                companyId = companyId,
                title = title,
                location = current.payload["location"],
                sourceUrl = current.payload["sourceUrl"],
                applyUrl = current.payload["applyUrl"],
                deadlineAt = current.payload["deadlineAt"],
                status = current.payload["status"] ?: "open",
            )
        )

        reviews[id] = current.copy(status = "approved", reviewedAt = nowIso())
        return created
    }

    override fun rejectReview(id: Long): ReviewQueueItem {
        val current = reviews[id] ?: error("review $id not found")
        require(current.status == "pending") { "review $id is already ${current.status}" }
        val rejected = current.copy(status = "rejected", reviewedAt = nowIso())
        reviews[id] = rejected
        return rejected
    }

    override fun runCrawler(): CrawlRunResult {
        val targets = companies.values.filter { it.active && !it.careersUrl.isNullOrBlank() }
        var queued = 0

        targets.forEach { company ->
            val careersUrl = company.careersUrl ?: return@forEach
            val pageTitle = fetchPageTitle(careersUrl)
            val inferredTitle = inferJobTitle(company.name, pageTitle)

            if (hasCrawlerDuplicate(company.id, inferredTitle, careersUrl)) {
                return@forEach
            }

            createReview(
                CreateReviewQueueRequest(
                    sourceType = "crawler.website",
                    payload = mapOf(
                        "companyId" to company.id.toString(),
                        "companyName" to company.name,
                        "title" to inferredTitle,
                        "location" to "Unknown",
                        "sourceUrl" to careersUrl,
                        "applyUrl" to careersUrl,
                        "status" to "open",
                    ),
                    confidence = if (pageTitle == null) 0.45 else 0.62,
                )
            )
            queued += 1
        }

        return CrawlRunResult(
            scannedCompanies = targets.size,
            queuedItems = queued,
        )
    }

    override fun overview(): Overview {
        val now = Instant.now()
        val upcomingDeadlines = applications.values.count {
            it.deadlineAt?.let { d -> runCatching { Instant.parse(d).isAfter(now) }.getOrDefault(false) } ?: false
        }

        val weekEnd = now.atOffset(ZoneOffset.UTC).plusDays(7).toInstant()
        val interviewsThisWeek = rounds.values.count {
            it.scheduledAt?.let { d ->
                runCatching {
                    val t = Instant.parse(d)
                    !t.isBefore(now) && !t.isAfter(weekEnd)
                }.getOrDefault(false)
            } ?: false
        }

        val pendingReviews = reviews.values.count { it.status == "pending" }

        return Overview(
            upcomingDeadlines = upcomingDeadlines,
            interviewsThisWeek = interviewsThisWeek,
            pendingReviews = pendingReviews,
        )
    }

    private fun hasCrawlerDuplicate(companyId: Long, title: String, careersUrl: String): Boolean {
        val hasPending = reviews.values.any {
            if (it.status != "pending") return@any false
            val payload = it.payload
            payload["companyId"] == companyId.toString() &&
                payload["title"] == title &&
                (payload["applyUrl"] == careersUrl || payload["sourceUrl"] == careersUrl)
        }

        if (hasPending) return true

        return jobs.values.any {
            it.companyId == companyId &&
                it.title == title &&
                (it.applyUrl == careersUrl || it.sourceUrl == careersUrl) &&
                it.status.equals("open", ignoreCase = true)
        }
    }

    private fun fetchPageTitle(url: String): String? {
        val request = runCatching {
            HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(8))
                .header("User-Agent", "FMROBot/0.1 (+personal use)")
                .GET()
                .build()
        }.getOrNull() ?: return null

        val body = runCatching {
            httpClient.send(request, HttpResponse.BodyHandlers.ofString()).body()
        }.getOrNull() ?: return null

        val match = titleRegex.find(body) ?: return null
        return match.groupValues[1].replace(Regex("\\s+"), " ").trim().takeIf { it.isNotBlank() }
    }

    private fun inferJobTitle(companyName: String, pageTitle: String?): String {
        val title = pageTitle?.lowercase().orEmpty()
        return when {
            "intern" in title -> "$companyName Intern"
            "career" in title || "job" in title || "join" in title -> "$companyName Robotics Engineer"
            else -> "$companyName Candidate Role (review needed)"
        }
    }
}
