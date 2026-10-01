// 슬라이드 p3-v2-nullable-as — as 와 nullable 값 형식, C# 2.0
using System;

class App
{
    static void Main()
    {
        object[] objs = new object[] { 5, "five", null };
        foreach (object o in objs)
        {
            int? n = o as int?;           // as needs a nullable target
            string s = n.HasValue ? "int " + n.Value : "not an int";
            Console.WriteLine(s);
        }
    }
}
