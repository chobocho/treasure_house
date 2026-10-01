// 슬라이드 p4-v3-linq-todict — ToDictionary 와 겹치는 키, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] names = { "Kim", "Lee", "Kang" };
        try
        {
            var d = names.ToDictionary(n => n[0]);
            Console.WriteLine(d.Count);
        }
        catch (ArgumentException e)
        {
            Console.WriteLine(e.Message);
        }

        ILookup<char, string> l = names.ToLookup(n => n[0]);
        Console.WriteLine("K: " + string.Join(" ", l['K']));
        Console.WriteLine("Z: " + l['Z'].Count() + " items");
    }
}
