// 슬라이드 p4-v3-linq-for-trap — for 변수를 잡은 쿼리, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string vowels = "aeiou";

        IEnumerable<char> q = "education";
        for (int i = 0; i < vowels.Length; i++)
        {
            q = q.Where(c => c != vowels[i]);
        }
        try
        {
            Console.WriteLine(new string(q.ToArray()));
        }
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }

        IEnumerable<char> r = "education";
        for (int i = 0; i < vowels.Length; i++)
        {
            char v = vowels[i];             // one variable per pass
            r = r.Where(c => c != v);
        }
        Console.WriteLine(new string(r.ToArray()));
    }
}
