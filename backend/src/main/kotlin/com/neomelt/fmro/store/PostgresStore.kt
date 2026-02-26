package com.neomelt.fmro.store

import com.neomelt.fmro.db.ApplicationsTable
import com.neomelt.fmro.db.CompaniesTable
import com.neomelt.fmro.db.InterviewRoundsTable
import com.neomelt.fmro.db.JobsTable
import com.neomelt.fmro.db.ReviewQueueTable
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
import kotlinx.serialization.builtins.MapSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.sql.ResultRow
import org.jetbrains.exposed.sql.SortOrder
import org.jetbrains.exposed.sql.SqlExpressionBuilder.eq
import org.jetbrains.exposed.sql.andWhere
import org.jetbrains.exposed.sql.deleteWhere
import org.jetbrains.exposed.sql.insert
import org.jetbrains.exposed.sql.selectAll
import org.jetbrains.exposed.sql.transactions.transaction
import org.jetbrains.exposed.sql.update
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration
import java.time.Instant
import java.time.ZoneOffset

object PostgresStore : FmroStore {
    private val json = Json
    private val mapSerializer = MapSerializer(String.serializer(), String.serializer())
    private val httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .followRedirects(HttpClient.Redirect.NORMAL)
        .build()
    private val titleRegex = Regex("(?is)<title[^>]*>(.*?)</title>")

    private data class CrawlPage(
        val statusCode: Int,
        val finalUrl: String?,
        val title: String?,
    )

    private fun nowIso(): String = Instant.now().toString()

    override fun listCompanies(): List<Company> = transaction {
        CompaniesTable.selectAll()
            .orderBy(CompaniesTable.id to SortOrder.ASC)
            .map { it.toCompany() }
    }

    override fun createCompany(req: CreateCompanyRequest): Company = transaction {
        val now = nowIso()
        val id = CompaniesTable.insert {
            it[name] = req.name.trim()
            it[officialSite] = req.officialSite
            it[careersUrl] = req.careersUrl
            it[active] = req.active
            it[createdAt] = now
            it[updatedAt] = now
        }[CompaniesTable.id].value

        CompaniesTable.selectAll().andWhere { CompaniesTable.id eq id }.single().toCompany()
    }

    override fun updateCompany(id: Long, req: UpdateCompanyRequest): Company? = transaction {
        val current = CompaniesTable.selectAll().andWhere { CompaniesTable.id eq id }.singleOrNull() ?: return@transaction null

        CompaniesTable.update({ CompaniesTable.id eq id }) {
            it[name] = req.name?.trim() ?: current[CompaniesTable.name]
            it[officialSite] = req.officialSite ?: current[CompaniesTable.officialSite]
            it[careersUrl] = req.careersUrl ?: current[CompaniesTable.careersUrl]
            it[active] = req.active ?: current[CompaniesTable.active]
            it[updatedAt] = nowIso()
        }

        CompaniesTable.selectAll().andWhere { CompaniesTable.id eq id }.single().toCompany()
    }

    override fun deleteCompany(id: Long): Boolean = transaction {
        CompaniesTable.deleteWhere { CompaniesTable.id eq id } > 0
    }

    override fun listJobs(companyId: Long?): List<JobPosting> = transaction {
        val query = JobsTable.selectAll()
        if (companyId != null) query.andWhere { JobsTable.companyId eq companyId }
        query.orderBy(JobsTable.id to SortOrder.ASC).map { it.toJobPosting() }
    }

    override fun createJob(req: CreateJobPostingRequest): JobPosting = transaction {
        val exists = CompaniesTable.selectAll().andWhere { CompaniesTable.id eq req.companyId }.any()
        require(exists) { "companyId ${req.companyId} does not exist" }

        val now = nowIso()
        val id = JobsTable.insert {
            it[companyId] = req.companyId
            it[title] = req.title.trim()
            it[location] = req.location
            it[sourceUrl] = req.sourceUrl
            it[applyUrl] = req.applyUrl
            it[deadlineAt] = req.deadlineAt
            it[status] = req.status
            it[sourcePlatform] = req.sourcePlatform
            it[firstSeenAt] = now
            it[lastSeenAt] = now
        }[JobsTable.id].value

        JobsTable.selectAll().andWhere { JobsTable.id eq id }.single().toJobPosting()
    }

    override fun updateJob(id: Long, req: UpdateJobPostingRequest): JobPosting? = transaction {
        val current = JobsTable.selectAll().andWhere { JobsTable.id eq id }.singleOrNull() ?: return@transaction null

        JobsTable.update({ JobsTable.id eq id }) {
            it[title] = req.title?.trim() ?: current[JobsTable.title]
            it[location] = req.location ?: current[JobsTable.location]
            it[sourceUrl] = req.sourceUrl ?: current[JobsTable.sourceUrl]
            it[applyUrl] = req.applyUrl ?: current[JobsTable.applyUrl]
            it[deadlineAt] = req.deadlineAt ?: current[JobsTable.deadlineAt]
            it[status] = req.status ?: current[JobsTable.status]
            it[sourcePlatform] = req.sourcePlatform ?: current[JobsTable.sourcePlatform]
            it[lastSeenAt] = nowIso()
        }

        JobsTable.selectAll().andWhere { JobsTable.id eq id }.single().toJobPosting()
    }

    override fun deleteJob(id: Long): Boolean = transaction {
        val deleted = JobsTable.deleteWhere { JobsTable.id eq id } > 0
        if (deleted) {
            ApplicationsTable.update({ ApplicationsTable.jobPostingId eq id }) {
                it[jobPostingId] = null
                it[updatedAt] = nowIso()
            }
        }
        deleted
    }

    override fun listApplications(stage: String?): List<JobApplication> = transaction {
        val query = ApplicationsTable.selectAll()
        if (stage != null) query.andWhere { ApplicationsTable.stage eq stage }
        query.orderBy(ApplicationsTable.id to SortOrder.ASC).map { it.toApplication() }
    }

    override fun createApplication(req: CreateApplicationRequest): JobApplication = transaction {
        if (req.jobPostingId != null) {
            val exists = JobsTable.selectAll().andWhere { JobsTable.id eq req.jobPostingId }.any()
            require(exists) { "jobPostingId ${req.jobPostingId} does not exist" }
        }

        val now = nowIso()
        val id = ApplicationsTable.insert {
            it[jobPostingId] = req.jobPostingId
            it[companyName] = req.companyName.trim()
            it[role] = req.role.trim()
            it[appliedAt] = req.appliedAt
            it[deadlineAt] = req.deadlineAt
            it[stage] = req.stage
            it[notes] = req.notes
            it[createdAt] = now
            it[updatedAt] = now
        }[ApplicationsTable.id].value

        ApplicationsTable.selectAll().andWhere { ApplicationsTable.id eq id }.single().toApplication()
    }

    override fun updateApplication(id: Long, req: UpdateApplicationRequest): JobApplication? = transaction {
        val current = ApplicationsTable.selectAll().andWhere { ApplicationsTable.id eq id }.singleOrNull()
            ?: return@transaction null

        ApplicationsTable.update({ ApplicationsTable.id eq id }) {
            it[companyName] = req.companyName?.trim() ?: current[ApplicationsTable.companyName]
            it[role] = req.role?.trim() ?: current[ApplicationsTable.role]
            it[appliedAt] = req.appliedAt ?: current[ApplicationsTable.appliedAt]
            it[deadlineAt] = req.deadlineAt ?: current[ApplicationsTable.deadlineAt]
            it[stage] = req.stage ?: current[ApplicationsTable.stage]
            it[notes] = req.notes ?: current[ApplicationsTable.notes]
            it[updatedAt] = nowIso()
        }

        ApplicationsTable.selectAll().andWhere { ApplicationsTable.id eq id }.single().toApplication()
    }

    override fun deleteApplication(id: Long): Boolean = transaction {
        ApplicationsTable.deleteWhere { ApplicationsTable.id eq id } > 0
    }

    override fun listRounds(applicationId: Long): List<InterviewRound> = transaction {
        InterviewRoundsTable.selectAll()
            .andWhere { InterviewRoundsTable.applicationId eq applicationId }
            .orderBy(InterviewRoundsTable.roundNo to SortOrder.ASC)
            .map { it.toRound() }
    }

    override fun createRound(applicationId: Long, req: CreateInterviewRoundRequest): InterviewRound = transaction {
        val appExists = ApplicationsTable.selectAll().andWhere { ApplicationsTable.id eq applicationId }.any()
        require(appExists) { "applicationId $applicationId does not exist" }

        val id = InterviewRoundsTable.insert {
            it[InterviewRoundsTable.applicationId] = applicationId
            it[roundNo] = req.roundNo
            it[scheduledAt] = req.scheduledAt
            it[outcome] = req.outcome
            it[note] = req.note
            it[createdAt] = nowIso()
        }[InterviewRoundsTable.id].value

        InterviewRoundsTable.selectAll().andWhere { InterviewRoundsTable.id eq id }.single().toRound()
    }

    override fun updateRound(id: Long, req: UpdateInterviewRoundRequest): InterviewRound? = transaction {
        val current = InterviewRoundsTable.selectAll().andWhere { InterviewRoundsTable.id eq id }.singleOrNull()
            ?: return@transaction null

        InterviewRoundsTable.update({ InterviewRoundsTable.id eq id }) {
            it[roundNo] = req.roundNo ?: current[InterviewRoundsTable.roundNo]
            it[scheduledAt] = req.scheduledAt ?: current[InterviewRoundsTable.scheduledAt]
            it[outcome] = req.outcome ?: current[InterviewRoundsTable.outcome]
            it[note] = req.note ?: current[InterviewRoundsTable.note]
        }

        InterviewRoundsTable.selectAll().andWhere { InterviewRoundsTable.id eq id }.single().toRound()
    }

    override fun deleteRound(id: Long): Boolean = transaction {
        InterviewRoundsTable.deleteWhere { InterviewRoundsTable.id eq id } > 0
    }

    override fun listReviewQueue(status: String?): List<ReviewQueueItem> = transaction {
        val query = ReviewQueueTable.selectAll()
        if (status != null) query.andWhere { ReviewQueueTable.status eq status }
        query.orderBy(ReviewQueueTable.id to SortOrder.DESC).map { it.toReview() }
    }

    override fun createReview(req: CreateReviewQueueRequest): ReviewQueueItem = transaction {
        val id = ReviewQueueTable.insert {
            it[sourceType] = req.sourceType
            it[payload] = json.encodeToString(mapSerializer, req.payload)
            it[confidence] = req.confidence
            it[status] = "pending"
            it[createdAt] = nowIso()
            it[reviewedAt] = null
        }[ReviewQueueTable.id].value

        ReviewQueueTable.selectAll().andWhere { ReviewQueueTable.id eq id }.single().toReview()
    }

    override fun approveReview(id: Long): JobPosting = transaction {
        val current = ReviewQueueTable.selectAll().andWhere { ReviewQueueTable.id eq id }.singleOrNull()
            ?: error("review $id not found")
        require(current[ReviewQueueTable.status] == "pending") { "review $id is already ${current[ReviewQueueTable.status]}" }

        val payload = runCatching {
            json.decodeFromString(mapSerializer, current[ReviewQueueTable.payload])
        }.getOrElse { emptyMap() }

        val companyId = payload["companyId"]?.toLongOrNull() ?: error("review $id missing valid companyId")
        val title = payload["title"]?.takeIf { it.isNotBlank() } ?: error("review $id missing title")

        val now = nowIso()
        val jobId = JobsTable.insert {
            it[JobsTable.companyId] = companyId
            it[JobsTable.title] = title
            it[location] = payload["location"]
            it[sourceUrl] = payload["sourceUrl"]
            it[applyUrl] = payload["applyUrl"]
            it[deadlineAt] = payload["deadlineAt"]
            it[status] = payload["status"] ?: "open"
            it[JobsTable.sourcePlatform] = payload["sourcePlatform"]
            it[firstSeenAt] = now
            it[lastSeenAt] = now
        }[JobsTable.id].value

        ReviewQueueTable.update({ ReviewQueueTable.id eq id }) {
            it[status] = "approved"
            it[reviewedAt] = nowIso()
        }

        JobsTable.selectAll().andWhere { JobsTable.id eq jobId }.single().toJobPosting()
    }

    override fun rejectReview(id: Long): ReviewQueueItem = transaction {
        val current = ReviewQueueTable.selectAll().andWhere { ReviewQueueTable.id eq id }.singleOrNull()
            ?: error("review $id not found")
        require(current[ReviewQueueTable.status] == "pending") { "review $id is already ${current[ReviewQueueTable.status]}" }

        ReviewQueueTable.update({ ReviewQueueTable.id eq id }) {
            it[status] = "rejected"
            it[reviewedAt] = nowIso()
        }

        ReviewQueueTable.selectAll().andWhere { ReviewQueueTable.id eq id }.single().toReview()
    }

    override fun runCrawler(): CrawlRunResult {
        val targets = listCompanies().filter { it.active && !it.careersUrl.isNullOrBlank() }
        var queued = 0

        targets.forEach { company ->
            val careersUrl = company.careersUrl ?: return@forEach
            val page = fetchPage(careersUrl) ?: return@forEach

            if (page.statusCode >= 400) {
                return@forEach
            }

            val targetUrl = page.finalUrl ?: careersUrl
            val inferredTitle = inferJobTitle(company.name, page.title)

            if (hasCrawlerDuplicate(company.id, inferredTitle, targetUrl)) {
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
                        "sourceUrl" to targetUrl,
                        "applyUrl" to targetUrl,
                        "status" to "open",
                    ),
                    confidence = if (page.title == null) 0.45 else 0.62,
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
        val applications = listApplications(stage = null)
        val rounds = transaction {
            InterviewRoundsTable.selectAll().map { it.toRound() }
        }

        val upcomingDeadlines = applications.count {
            it.deadlineAt?.let { d -> runCatching { Instant.parse(d).isAfter(now) }.getOrDefault(false) } ?: false
        }

        val weekEnd = now.atOffset(ZoneOffset.UTC).plusDays(7).toInstant()
        val interviewsThisWeek = rounds.count {
            it.scheduledAt?.let { d ->
                runCatching {
                    val t = Instant.parse(d)
                    !t.isBefore(now) && !t.isAfter(weekEnd)
                }.getOrDefault(false)
            } ?: false
        }

        val pendingReviews = listReviewQueue("pending").size

        return Overview(
            upcomingDeadlines = upcomingDeadlines,
            interviewsThisWeek = interviewsThisWeek,
            pendingReviews = pendingReviews,
        )
    }

    private fun hasCrawlerDuplicate(companyId: Long, title: String, careersUrl: String): Boolean = transaction {
        val hasOpenJob = JobsTable.selectAll()
            .andWhere { JobsTable.companyId eq companyId }
            .andWhere { JobsTable.title eq title }
            .andWhere { JobsTable.status eq "open" }
            .any {
                it[JobsTable.applyUrl] == careersUrl || it[JobsTable.sourceUrl] == careersUrl
            }

        if (hasOpenJob) return@transaction true

        ReviewQueueTable.selectAll()
            .andWhere { ReviewQueueTable.status eq "pending" }
            .any { row ->
                val payload = runCatching {
                    json.decodeFromString(mapSerializer, row[ReviewQueueTable.payload])
                }.getOrElse { emptyMap() }

                payload["companyId"] == companyId.toString() &&
                    payload["title"] == title &&
                    (payload["applyUrl"] == careersUrl || payload["sourceUrl"] == careersUrl)
            }
    }

    private fun fetchPage(url: String): CrawlPage? {
        val request = runCatching {
            HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(8))
                .header("User-Agent", "FMROBot/0.1 (+personal use)")
                .GET()
                .build()
        }.getOrNull() ?: return null

        val response = runCatching {
            httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        }.getOrNull() ?: return null

        val body = response.body().orEmpty()
        val title = titleRegex.find(body)
            ?.groupValues
            ?.getOrNull(1)
            ?.replace(Regex("\\s+"), " ")
            ?.trim()
            ?.takeIf { it.isNotBlank() }

        return CrawlPage(
            statusCode = response.statusCode(),
            finalUrl = response.uri()?.toString(),
            title = title,
        )
    }

    private fun inferJobTitle(companyName: String, pageTitle: String?): String {
        val title = pageTitle?.lowercase().orEmpty()
        return when {
            "intern" in title -> "$companyName Intern"
            "career" in title || "job" in title || "join" in title -> "$companyName Robotics Engineer"
            else -> "$companyName Candidate Role (review needed)"
        }
    }

    private fun ResultRow.toCompany(): Company = Company(
        id = this[CompaniesTable.id].value,
        name = this[CompaniesTable.name],
        officialSite = this[CompaniesTable.officialSite],
        careersUrl = this[CompaniesTable.careersUrl],
        active = this[CompaniesTable.active],
        createdAt = this[CompaniesTable.createdAt],
        updatedAt = this[CompaniesTable.updatedAt],
    )

    private fun ResultRow.toJobPosting(): JobPosting = JobPosting(
        id = this[JobsTable.id].value,
        companyId = this[JobsTable.companyId].value,
        title = this[JobsTable.title],
        location = this[JobsTable.location],
        sourceUrl = this[JobsTable.sourceUrl],
        applyUrl = this[JobsTable.applyUrl],
        deadlineAt = this[JobsTable.deadlineAt],
        status = this[JobsTable.status],
        sourcePlatform = this[JobsTable.sourcePlatform],
        firstSeenAt = this[JobsTable.firstSeenAt],
        lastSeenAt = this[JobsTable.lastSeenAt],
    )

    private fun ResultRow.toApplication(): JobApplication = JobApplication(
        id = this[ApplicationsTable.id].value,
        jobPostingId = this[ApplicationsTable.jobPostingId]?.value,
        companyName = this[ApplicationsTable.companyName],
        role = this[ApplicationsTable.role],
        appliedAt = this[ApplicationsTable.appliedAt],
        deadlineAt = this[ApplicationsTable.deadlineAt],
        stage = this[ApplicationsTable.stage],
        notes = this[ApplicationsTable.notes],
        createdAt = this[ApplicationsTable.createdAt],
        updatedAt = this[ApplicationsTable.updatedAt],
    )

    private fun ResultRow.toRound(): InterviewRound = InterviewRound(
        id = this[InterviewRoundsTable.id].value,
        applicationId = this[InterviewRoundsTable.applicationId].value,
        roundNo = this[InterviewRoundsTable.roundNo],
        scheduledAt = this[InterviewRoundsTable.scheduledAt],
        outcome = this[InterviewRoundsTable.outcome],
        note = this[InterviewRoundsTable.note],
        createdAt = this[InterviewRoundsTable.createdAt],
    )

    private fun ResultRow.toReview(): ReviewQueueItem {
        val payload = runCatching {
            json.decodeFromString(mapSerializer, this[ReviewQueueTable.payload])
        }.getOrElse { emptyMap() }

        return ReviewQueueItem(
            id = this[ReviewQueueTable.id].value,
            sourceType = this[ReviewQueueTable.sourceType],
            payload = payload,
            confidence = this[ReviewQueueTable.confidence],
            status = this[ReviewQueueTable.status],
            createdAt = this[ReviewQueueTable.createdAt],
            reviewedAt = this[ReviewQueueTable.reviewedAt],
        )
    }
}
