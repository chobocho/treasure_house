// 슬라이드 p11-v10-filens — 파일 범위 네임스페이스, C# 10.0
namespace Shop.Billing;

using System;

class Invoice
{
    public string Describe() => GetType().FullName;
}

class App
{
    static void Main() => Console.WriteLine(new Invoice().Describe());
}
