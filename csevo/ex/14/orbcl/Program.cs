// 슬라이드 p14-v13-or-bcl — 참조 어셈블리의 우선순위 특성, C# 13
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.InteropServices;
using MDH = System.Reflection.Metadata.MethodDefinitionHandle;
using TDH = System.Reflection.Metadata.TypeDefinitionHandle;
using TRH = System.Reflection.Metadata.TypeReferenceHandle;

class Program
{
    static string Name(MetadataReader md, EntityHandle t) =>
        t.Kind == HandleKind.TypeDefinition
        ? md.GetString(md.GetTypeDefinition((TDH)t).Name)
        : md.GetString(md.GetTypeReference((TRH)t).Name);

    static EntityHandle Owner(MetadataReader md, EntityHandle c) =>
        c.Kind == HandleKind.MethodDefinition
        ? md.GetMethodDefinition((MDH)c).GetDeclaringType()
        : md.GetMemberReference((MemberReferenceHandle)c).Parent;

    static void Main()
    {
        string dir = Path.Combine(RuntimeEnvironment
            .GetRuntimeDirectory(), "../../../packs",
            "Microsoft.NETCore.App.Ref", Environment.Version.ToString(),
            "ref/net10.0");
        var seen = new SortedDictionary<string, List<string>>();
        foreach (string f in Directory.GetFiles(dir, "*.dll"))
        {
            using var pe = new PEReader(File.OpenRead(f));
            MetadataReader md = pe.GetMetadataReader();
            foreach (CustomAttributeHandle h in md.CustomAttributes)
            {
                CustomAttribute ca = md.GetCustomAttribute(h);
                if (Name(md, Owner(md, ca.Constructor))
                    != "OverloadResolutionPriorityAttribute") continue;
                var m = md.GetMethodDefinition((MDH)ca.Parent);
                BlobReader b = md.GetBlobReader(ca.Value);
                b.ReadUInt16();                      // prolog 0x0001
                string key = Path.GetFileNameWithoutExtension(f)
                    + " " + Name(md, m.GetDeclaringType())
                    + " " + b.ReadInt32();
                if (!seen.ContainsKey(key)) seen[key] = [];
                seen[key].Add(md.GetString(m.Name));
            }
        }
        foreach (var kv in seen)
            Console.WriteLine(kv.Key + " x" + kv.Value.Count + ": " +
                string.Join(" ", kv.Value.Distinct().Order().Take(3)));
    }
}
