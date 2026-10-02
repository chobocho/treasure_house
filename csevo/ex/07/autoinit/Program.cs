// 슬라이드 p7-v6-autoinit — 자동 속성 초기화자, C# 6.0
using System;
using System.Collections.Generic;

class Student
{
    public string Name { get; set; } = "(none)";
    public List<int> Grades { get; set; } = new List<int>();
    public static int Seats { get; set; } = 30;
}

class Program
{
    static void Main()
    {
        Student s = new Student();
        s.Grades.Add(90);
        Console.WriteLine(s.Name + " " + s.Grades.Count);
        Console.WriteLine(Student.Seats);
    }
}
