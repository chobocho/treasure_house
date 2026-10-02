// 슬라이드 p8-v7-decon — 분해 선언과 분해 대입, C# 7.0
using System;

class App
{
    static (string, int, double) City() => ("Seoul", 9411, 605.2);

    static void Main()
    {
        (string name, int pop, double area) = City();  // declarations
        Console.WriteLine(name + " " + pop + " " + area);

        (var n2, var p2, var a2) = City();             // var inside
        var (n3, p3, a3) = City();                     // var outside
        Console.WriteLine(n2 == n3 && p2 == p3 && a2 == a3);

        string n; int p; double a;
        (n, p, a) = City();                            // assignment
        Console.WriteLine(n.ToUpper() + " " + (p + 1));
    }
}
