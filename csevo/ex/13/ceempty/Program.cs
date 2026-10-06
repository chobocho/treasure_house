// 슬라이드 p13-v12-ce-empty — 빈 컬렉션 식 [], C# 12
using System;
using System.Collections.Generic;

class Program
{
    static int[] Arr() => [];
    static IEnumerable<int> Seq() => [];
    static List<int> Lst() => [];
    static IList<int> Mut() => [];

    static void Main()
    {
        Console.WriteLine("int[]       " +
            ReferenceEquals(Arr(), Array.Empty<int>()));
        Console.WriteLine("IEnumerable " +
            ReferenceEquals(Seq(), Array.Empty<int>()) + " " +
            Seq().GetType().Name);
        Console.WriteLine("List<int>   " +
            ReferenceEquals(Lst(), Lst()));
        Console.WriteLine("IList<int>  " +
            ReferenceEquals(Mut(), Mut()) + " " + Mut().GetType().Name);
        Span<int> s = [];
        Console.WriteLine("Span<int>   " + s.Length);
    }
}
