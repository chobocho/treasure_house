// 슬라이드 p2-v1-strobj — object 로 보면 == 은 참조 비교, C# 1.0
using System;

class App
{
    static void Main()
    {
        string a = "hello";
        char[] cs = { 'h', 'e', 'l', 'l', 'o' };
        object c = new string(cs);
        Console.WriteLine(a == c);            // object == : references
        Console.WriteLine(a.Equals(c));       // String.Equals: values
        Console.WriteLine(a == (string)c);    // string == : values
    }
}
