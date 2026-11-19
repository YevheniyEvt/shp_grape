"use client";

import { PrinterIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useT } from "@/i18n/client";

export function PrintButton() {
  const { t } = useT();
  return (
    <Button variant="outline" size="sm" onClick={() => window.print()} className="print:hidden">
      <PrinterIcon aria-hidden="true" />
      {t("Print")}
    </Button>
  );
}
