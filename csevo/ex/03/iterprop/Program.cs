// 슬라이드 p3-v2-iterator-accessor — 접근자도 반복기가 된다, C# 2.0
using System;
using System.Collections.Generic;

class Week
{
    string[] days = new string[] { "Mon", "Tue", "Wed", "Thu", "Fri" };

    public IEnumerable<string> Weekdays
    {
        get
        {
            foreach (string d in days) yield return d;
        }
    }

    public IEnumerable<string> Every(int step)
    {
        for (int i = 0; i < days.Length; i += step)
        {
            yield return days[i];
        }
    }
}

class App
{
    static void Main()
    {
        Week w = new Week();
        List<string> all = new List<string>(w.Weekdays);
        Console.WriteLine(string.Join(" ", all.ToArray()));
        foreach (string d in w.Every(2)) Console.Write(d + " ");
        Console.WriteLine();
    }
}
