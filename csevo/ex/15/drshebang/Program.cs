// 슬라이드 p15-v14-dr-shebang — 첫 줄이 아닌 #!, C# 14
#!/usr/bin/env -S dotnet run
#:property LangVersion=14
#:package Humanizer@2.14.1
using System;

class Program
{
    static void Main() => Console.WriteLine("ran");
}
