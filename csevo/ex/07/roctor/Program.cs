// 슬라이드 p7-v6-roauto-ctor — 생성자 밖에서는 대입 불가, C# 6.0
using System;

class Student
{
    public string Last { get; }

    public Student(string last)
    {
        Last = "?";
        Last = last;        // twice in the constructor: fine
    }

    public void ChangeName(string newLast)
    {
#if BAD
        Last = newLast;     // CS0200 in the documentation
#endif
    }

#if BAD2
    public Student() : this("x")
    {
        Action set = () => Last = "y";   // a lambda in the constructor
    }
#endif
}

class Program
{
    static void Main()
    {
        Console.WriteLine(new Student("Hopper").Last);
    }
}
