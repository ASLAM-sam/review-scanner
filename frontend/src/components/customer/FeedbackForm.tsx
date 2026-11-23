"use client";

import React, { useState } from "react";
import { StepProgress } from "./StepProgress";
import { StepWelcome } from "./StepWelcome";
import { StepRatings } from "./StepRatings";
import { StepPrompts } from "./StepPrompts";
import { StepComments } from "./StepComments";
import { StepSuccess } from "./StepSuccess";
import { Card, CardContent } from "@/components/ui/Card";
import type { FeedbackSubmissionPayload, PublicRestaurantInfo } from "@/types";

interface FeedbackFormProps {
  sessionId: string;
  restaurant: PublicRestaurantInfo;
  onSubmit: (payload: FeedbackSubmissionPayload) => Promise<boolean>;
  isSubmitting?: boolean;
}

export function FeedbackForm({
  sessionId,
  restaurant,
  onSubmit,
  isSubmitting = false,
}: FeedbackFormProps) {
  // Wizard step: 1 = Welcome, 2 = Ratings, 3 = Smart Statements & Prompts, 4 = Comments, 5 = Success
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Form state - Start unselected per requirements (NO preselection of 5 stars)
  const [selectedSentiment, setSelectedSentiment] = useState<"positive" | "neutral" | "negative" | null>(null);
  const [foodRating, setFoodRating] = useState<number>(0);
  const [serviceRating, setServiceRating] = useState<number>(0);
  const [ambienceRating, setAmbienceRating] = useState<number>(0);
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>([]);
  const [notes, setNotes] = useState<string>("");
  const [submissionError, setSubmissionError] = useState<string>("");
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  const primaryColor = restaurant.primary_color || "#16a34a";

  const handleSelectSentiment = (sentiment: "positive" | "neutral" | "negative") => {
    setSelectedSentiment(sentiment);
    // Smoothly auto-advance to Step 2 when a sentiment is chosen
    setCurrentStep(2);
  };

  const handleTogglePrompt = (promptText: string) => {
    setSelectedPrompts((prev) =>
      prev.includes(promptText)
        ? prev.filter((p) => p !== promptText)
        : [...prev, promptText]
    );
  };

  const handleSubmitFeedback = async () => {
    setSubmissionError("");

    // Final validation
    if (foodRating < 1 || serviceRating < 1 || ambienceRating < 1) {
      setSubmissionError("Please rate food, service, and ambience before submitting.");
      setCurrentStep(2);
      return;
    }

    // Determine overall experience
    const avg = (foodRating + serviceRating + ambienceRating) / 3;
    let resolvedExperience: "positive" | "neutral" | "negative" = "positive";
    if (avg >= 3.8) {
      resolvedExperience = "positive";
    } else if (avg >= 2.8) {
      resolvedExperience = selectedSentiment || "neutral";
    } else {
      resolvedExperience = "negative";
    }

    const payload: FeedbackSubmissionPayload = {
      session_id: sessionId,
      food_rating: foodRating,
      service_rating: serviceRating,
      ambience_rating: ambienceRating,
      overall_experience: resolvedExperience,
      positive_tags: [],
      improvement_tags: [],
      selected_prompts: selectedPrompts,
      customer_notes: notes.trim(),
    };

    const success = await onSubmit(payload);
    if (success) {
      setIsSubmitted(true);
      setCurrentStep(5);
    } else {
      setSubmissionError("We could not save your feedback. Please check your connection and retry.");
    }
  };

  const getStepTitle = (step: number) => {
    switch (step) {
      case 1:
        return "Welcome";
      case 2:
        return "Experience Ratings";
      case 3:
        return "Smart Statements";
      case 4:
        return "Additional Remarks";
      default:
        return "Complete";
    }
  };

  if (isSubmitted || currentStep === 5) {
    return (
      <StepSuccess
        restaurant={restaurant}
        sessionId={sessionId}
        foodRating={foodRating}
        serviceRating={serviceRating}
        ambienceRating={ambienceRating}
      />
    );
  }

  return (
    <Card className="border-slate-100 shadow-sm overflow-hidden bg-white">
      <CardContent className="p-5 sm:p-7">
        {/* Step Progress Bar (shown on steps 2 to 4) */}
        {currentStep > 1 && (
          <StepProgress
            currentStep={currentStep}
            totalSteps={4}
            stepTitle={getStepTitle(currentStep)}
            onBack={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            primaryColor={primaryColor}
          />
        )}

        {/* Step 1: Welcome Screen */}
        {currentStep === 1 && (
          <StepWelcome
            restaurant={restaurant}
            selectedSentiment={selectedSentiment}
            onSelectSentiment={handleSelectSentiment}
            onContinue={() => setCurrentStep(2)}
          />
        )}

        {/* Step 2: Experience Ratings */}
        {currentStep === 2 && (
          <StepRatings
            foodRating={foodRating}
            serviceRating={serviceRating}
            ambienceRating={ambienceRating}
            onFoodChange={setFoodRating}
            onServiceChange={setServiceRating}
            onAmbienceChange={setAmbienceRating}
            onContinue={() => setCurrentStep(3)}
            primaryColor={primaryColor}
          />
        )}

        {/* Step 3: Smart Prompts Library */}
        {currentStep === 3 && (
          <StepPrompts
            foodRating={foodRating}
            serviceRating={serviceRating}
            ambienceRating={ambienceRating}
            selectedPrompts={selectedPrompts}
            onTogglePrompt={handleTogglePrompt}
            onContinue={() => setCurrentStep(4)}
            primaryColor={primaryColor}
          />
        )}

        {/* Step 4: Optional Remarks & Submit */}
        {currentStep === 4 && (
          <StepComments
            restaurantName={restaurant.name}
            notes={notes}
            onNotesChange={setNotes}
            foodRating={foodRating}
            serviceRating={serviceRating}
            ambienceRating={ambienceRating}
            selectedPrompts={selectedPrompts}
            onSubmit={handleSubmitFeedback}
            isSubmitting={isSubmitting}
            submissionError={submissionError}
            onClearError={() => setSubmissionError("")}
            primaryColor={primaryColor}
          />
        )}
      </CardContent>
    </Card>
  );
}
