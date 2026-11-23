import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContactForm } from "@/components/content/contact-form";
import { I18nProvider } from "@/i18n/client";

import { PreorderForm } from "./preorder-form";

const sendPreorder = vi.fn();
const sendContactMessage = vi.fn();
vi.mock("@/lib/api/orders", () => ({
  sendPreorder: (...args: unknown[]) => sendPreorder(...args),
  sendContactMessage: (...args: unknown[]) => sendContactMessage(...args),
}));

const wrap = (children: ReactNode) => (
  <I18nProvider locale="en" catalog={{ catalog: {}, plural: null }}>
    {children}
  </I18nProvider>
);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("PreorderForm", () => {
  it("sends a pre-order and thanks the customer", async () => {
    sendPreorder.mockResolvedValue(null);
    render(wrap(<PreorderForm />));
    const user = userEvent.setup();

    const phone = screen.getByLabelText(/^Phone/);
    await user.click(phone);
    expect(phone).toHaveValue("+380 ");
    await user.type(phone, "671234567");
    await user.type(screen.getByLabelText(/Full name/), "Оля");
    await user.type(screen.getByLabelText(/What would you like/), "Рубін — 5 саджанців");
    await user.click(screen.getByRole("button", { name: /Send the pre-order/ }));

    expect(await screen.findByText("Thank you! Your pre-order is sent.")).toBeInTheDocument();
    expect(sendPreorder).toHaveBeenCalledWith(
      {
        full_name: "Оля",
        phone: "+380 (67) 123-45-67",
        email: "",
        description: "Рубін — 5 саджанців",
        website: "",
      },
      "en",
    );
  });

  it("shows validation and server errors", async () => {
    sendPreorder.mockResolvedValueOnce({ kind: "validation", fields: { phone: "Bad phone." } });
    sendPreorder.mockResolvedValueOnce({ kind: "network" });
    render(wrap(<PreorderForm />));
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /Send the pre-order/ }));
    expect(await screen.findAllByText("This field is required.")).toHaveLength(2);
    expect(sendPreorder).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText(/Full name/), "Оля");
    await user.type(screen.getByLabelText(/^Phone/), "0671234567");
    await user.type(screen.getByLabelText(/What would you like/), "Рубін");
    await user.click(screen.getByRole("button", { name: /Send the pre-order/ }));
    expect(await screen.findByText("Bad phone.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Send the pre-order/ }));
    expect(await screen.findByText(/No connection to the server/)).toBeInTheDocument();
  });
});

describe("ContactForm", () => {
  it("sends a message", async () => {
    sendContactMessage.mockResolvedValue(null);
    render(wrap(<ContactForm />));
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/Your name/), "Петро");
    await user.type(screen.getByLabelText(/Email/), "petro@example.com");
    await user.type(screen.getByLabelText(/Message/), "Привіт!");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Thank you! Your message is sent.")).toBeInTheDocument();
    expect(sendContactMessage).toHaveBeenCalledWith(
      { name: "Петро", email: "petro@example.com", subject: "", message: "Привіт!", website: "" },
      "en",
    );
  });

  it("explains a server failure", async () => {
    sendContactMessage.mockResolvedValue({ kind: "server" });
    render(wrap(<ContactForm />));
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/Your name/), "Петро");
    await user.type(screen.getByLabelText(/Email/), "petro@example.com");
    await user.type(screen.getByLabelText(/Message/), "Привіт!");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong");
  });
});
