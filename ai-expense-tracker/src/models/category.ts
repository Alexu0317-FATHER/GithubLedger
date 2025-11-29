class Category {
    id: number;
    name: string;

    constructor(id: number, name: string) {
        this.id = id;
        this.name = name;
    }

    validateName(): boolean {
        return this.name.length > 0;
    }
}

export default Category;