package com.neomelt.fmro.db

import org.jetbrains.exposed.dao.id.LongIdTable
import org.jetbrains.exposed.sql.ReferenceOption

object CompaniesTable : LongIdTable("company") {
    val name = text("name").uniqueIndex()
    val officialSite = text("official_site").nullable()
    val careersUrl = text("careers_url").nullable()
    val active = bool("active").default(true)
    val createdAt = text("created_at")
    val updatedAt = text("updated_at")
}

object JobsTable : LongIdTable("job_posting") {
    val companyId = reference("company_id", CompaniesTable, onDelete = ReferenceOption.CASCADE)
    val title = text("title")
    val location = text("location").nullable()
    val sourceUrl = text("source_url").nullable()
    val applyUrl = text("apply_url").nullable()
    val deadlineAt = text("deadline_at").nullable()
    val status = text("status").default("open")
    val sourcePlatform = text("source_platform").nullable()
    val firstSeenAt = text("first_seen_at")
    val lastSeenAt = text("last_seen_at")
}

object ApplicationsTable : LongIdTable("application") {
    val jobPostingId = reference("job_posting_id", JobsTable, onDelete = ReferenceOption.SET_NULL).nullable()
    val companyName = text("company_name")
    val role = text("role")
    val appliedAt = text("applied_at").nullable()
    val deadlineAt = text("deadline_at").nullable()
    val stage = text("stage").default("applied")
    val notes = text("notes").nullable()
    val createdAt = text("created_at")
    val updatedAt = text("updated_at")
}

object InterviewRoundsTable : LongIdTable("interview_round") {
    val applicationId = reference("application_id", ApplicationsTable, onDelete = ReferenceOption.CASCADE)
    val roundNo = integer("round_no")
    val scheduledAt = text("scheduled_at").nullable()
    val outcome = text("outcome").nullable()
    val note = text("note").nullable()
    val createdAt = text("created_at")
}

object ReviewQueueTable : LongIdTable("review_queue") {
    val sourceType = text("source_type")
    val payload = text("payload")
    val confidence = double("confidence").nullable()
    val status = text("status").default("pending")
    val createdAt = text("created_at")
    val reviewedAt = text("reviewed_at").nullable()
}
