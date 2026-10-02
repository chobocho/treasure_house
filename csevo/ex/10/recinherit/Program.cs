// 슬라이드 p10-v9-rec-inherit — 레코드의 상속, C# 9.0
using System;

public abstract record Person(string FirstName, string LastName);
public record Teacher(string FirstName, string LastName, int Grade)
    : Person(FirstName, LastName);
public record Student(string FirstName, string LastName, int Grade)
    : Person(FirstName, LastName);

class App
{
    static void Main()
    {
        Person teacher = new Teacher("Nancy", "Davolio", 3);
        Person student = new Student("Nancy", "Davolio", 3);
        Student student2 = new Student("Nancy", "Davolio", 3);
        Console.WriteLine(teacher == student);  // run-time types differ
        Console.WriteLine(student == student2); // Person vs Student var
        Console.WriteLine(teacher);              // derived members too
        var (first, last) = student;             // Person.Deconstruct
        Console.WriteLine(first + " " + last);
    }
}
