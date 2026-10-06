// 슬라이드 p13-v12-pc-unread — 읽지 않은 매개변수, C# 12.0
using System;

class Logger(string name, int level)
{
    public string Name => name;
#if !UNREAD
    public bool Verbose => level > 1;
#endif
}

class App
{
    static void Main() => Console.WriteLine(new Logger("app", 2).Name);
}
