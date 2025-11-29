export class Expense {
    id: number;
    amount: number;
    date: Date;
    category: string;

    constructor(id: number, amount: number, date: Date, category: string) {
        this.id = id;
        this.amount = amount;
        this.date = date;
        this.category = category;
    }

    validate(): boolean {
        if (this.amount <= 0) {
            throw new Error("Amount must be greater than zero.");
        }
        if (!this.date || isNaN(this.date.getTime())) {
            throw new Error("Invalid date.");
        }
        if (!this.category) {
            throw new Error("Category is required.");
        }
        return true;
    }
}