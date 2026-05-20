-- CreateTable
CREATE TABLE "DeletedClaim" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "originalId" TEXT NOT NULL,
    "text" TEXT NOT NULL,
    "ctId" TEXT NOT NULL,
    "source" TEXT,
    "verdict" TEXT NOT NULL,
    "score" REAL NOT NULL,
    "deletedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
