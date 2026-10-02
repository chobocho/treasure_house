// 슬라이드 p7-v6-roauto — get 만 있는 자동 속성, C# 6.0
using System;

class Student
{
    public string First { get; }
    public string Last { get; }

    public Student(string first, string last)
    {
        First = first;     // allowed only in a constructor
        Last = last;
    }
}

class Program
{
    static void Main()
    {
        Student s = new Student("Grace", "Hopper");
        Console.WriteLine(s.First + " " + s.Last);
    }
}
