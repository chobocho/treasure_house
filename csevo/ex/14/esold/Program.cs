// 슬라이드 p14-v13-es-old — C# 12 까지의 ESC, 그리고 #if 안의 \e, C# 12
using System;

class Program
{
    static void Main()
    {
        string a = "\u001b[0m";         // four hex digits, always
        string b = "\U0000001b[0m";     // eight hex digits
        string c = "\x1b[0m";           // one to four hex digits
        string d = (char)27 + "[0m";
        Console.WriteLine(a == b && b == c && c == d);
#if CS13
        string e = "\e[0m";             // only when CS13 is defined
        Console.WriteLine(a == e);
#endif
    }
}
