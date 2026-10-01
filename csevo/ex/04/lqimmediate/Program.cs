// 슬라이드 p4-v3-linq-eager — 부를 때·첫 원소 때 꺼낸 수, C# 3.0
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static int pulled;

    static IEnumerable<int> Src()
    {
        for (int i = 1; i <= 4; i++)
        {
            pulled++;
            yield return i;
        }
    }

    static void Try(string name, Func<IEnumerable<int>, object> op)
    {
        pulled = 0;
        object r = op(Src());
        string line = name.PadRight(12) + "call " + pulled;
        IEnumerable seq = r as IEnumerable;
        if (seq != null)
        {
            seq.GetEnumerator().MoveNext();
            line += ", first item " + pulled;
        }
        Console.WriteLine(line);
    }

    static void Main()
    {
        Try("Where", s => s.Where(x => x > 1));
        Try("Select", s => s.Select(x => x * 2));
        Try("Take(2)", s => s.Take(2));
        Try("Distinct", s => s.Distinct());
        Try("OrderBy", s => s.OrderBy(x => -x));
        Try("Reverse", s => s.Reverse());
        Try("GroupBy", s => s.GroupBy(x => x % 2));
        Try("ToList", s => s.ToList());
        Try("Count", s => s.Count());
        Try("First", s => s.First());
        Try("Any", s => s.Any());
        Try("Contains(2)", s => s.Contains(2));
    }
}
