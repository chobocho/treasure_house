// 슬라이드 p4-v3-linq-oftype — Cast 는 던지고 OfType 은 거른다, C# 3.0
using System;
using System.Collections;
using System.Linq;

class Program
{
    static void Main()
    {
        ArrayList mixed = new ArrayList { "a", 1, "b", 2.5 };

        Console.WriteLine("OfType: "
            + string.Join(" ", mixed.OfType<string>()));

        Console.Write("Cast:   ");
        try
        {
            foreach (string s in mixed.Cast<string>())
            {
                Console.Write(s + " ");
            }
        }
        catch (InvalidCastException)
        {
            Console.WriteLine("<InvalidCastException>");
        }
    }
}
