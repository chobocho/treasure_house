// 슬라이드 p2-v1-fixedstr — string 을 fixed 로 고정하기, C# 7.3
using System;

class App
{
    static unsafe void Main()
    {
        bool has = typeof(string).GetMethod("GetPinnableReference")
            != null;
        Console.WriteLine("string.GetPinnableReference: " + has);
        string s = "hello";
        fixed (char* c = s)                    // pins the characters
        {
            int n = 0;
            while (c[n] != '\0') n++;          // NUL after the last one
            Console.WriteLine("length via pointer = " + n);
        }
    }
}
