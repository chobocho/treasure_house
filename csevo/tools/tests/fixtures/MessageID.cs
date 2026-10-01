        internal static LanguageVersion RequiredVersion(this MessageID feature)
        {
            Debug.Assert(RequiredFeature(feature) == null);

            // Based on CSourceParser::GetFeatureUsage from SourceParser.cpp.
            // Checks are in the LanguageParser unless otherwise noted.
            switch (feature)
            {
                // PREFER reporting diagnostics in binding when diagnostics do not affect the shape of the syntax tree

                // C# preview features.
                //return LanguageVersion.Preview;

                // C# 13.0 features.
                case MessageID.IDS_FeatureFieldKeyword:
                case MessageID.IDS_FeatureFirstClassSpan:
                case MessageID.IDS_FeatureUnboundGenericTypesInNameof:
                case MessageID.IDS_FeatureSimpleLambdaParameterModifiers:
                case MessageID.IDS_FeaturePartialEventsAndConstructors:
                case MessageID.IDS_FeatureExtensions:
                case MessageID.IDS_FeatureNullConditionalAssignment:
                case MessageID.IDS_FeatureExpressionOptionalAndNamedArguments:
                case MessageID.IDS_FeatureUserDefinedCompoundAssignmentOperators:
                    return LanguageVersion.CSharp14;

                // C# 13.0 features.
                case MessageID.IDS_FeatureStringEscapeCharacter: // lexer check
                case MessageID.IDS_FeatureImplicitIndexerInitializer:
                case MessageID.IDS_FeatureLockObject:
                case MessageID.IDS_FeatureParamsCollections:
                case MessageID.IDS_FeatureRefUnsafeInIteratorAsync:
                case MessageID.IDS_FeatureRefStructInterfaces:
                case MessageID.IDS_FeatureAllowsRefStructConstraint:
                case MessageID.IDS_FeaturePartialProperties:
                case MessageID.IDS_FeatureOverloadResolutionPriority:
                    return LanguageVersion.CSharp13;
                case MessageID.IDS_FeatureMemberNotNull:
                case MessageID.IDS_FeatureAndPattern: // semantic check
                case MessageID.IDS_FeatureNotPattern: // semantic check
                case MessageID.IDS_FeatureOrPattern: // semantic check
                case MessageID.IDS_FeatureParenthesizedPattern: // semantic check
                case MessageID.IDS_FeatureTypePattern: // semantic check
                case MessageID.IDS_FeatureRelationalPattern: // semantic check
                case MessageID.IDS_FeatureExtensionGetEnumerator: // semantic check
                case MessageID.IDS_FeatureExtensionGetAsyncEnumerator: // semantic check
                case MessageID.IDS_FeatureNativeInt:
                case MessageID.IDS_FeatureExtendedPartialMethods: // semantic check
                case MessageID.IDS_TopLevelStatements:
                case MessageID.IDS_FeatureInitOnlySetters: // semantic check
                case MessageID.IDS_FeatureRecords: // semantic check
                case MessageID.IDS_FeatureTargetTypedConditional:  // semantic check
                case MessageID.IDS_FeatureCovariantReturnsForOverrides: // semantic check
                case MessageID.IDS_FeatureStaticAnonymousFunction: // semantic check
                case MessageID.IDS_FeatureModuleInitializers: // semantic check on method attribute
                case MessageID.IDS_FeatureDefaultTypeParameterConstraint: // semantic check
                case MessageID.IDS_FeatureVarianceSafetyForStaticInterfaceMembers: // semantic check
                    return LanguageVersion.CSharp9;
                case MessageID.IDS_FeatureNullable:
                case MessageID.IDS_FeaturePragma: // Checked in the directive parser.
                case MessageID.IDS_FeatureSwitchOnBool: // Checked in the binder.
                    return LanguageVersion.CSharp2;

                // Special C# 2 feature: only a warning in C# 1.
                case MessageID.IDS_FeatureModuleAttrLoc:
                    return LanguageVersion.CSharp1;

                default:
                    throw ExceptionUtilities.UnexpectedValue(feature);
            }
        }
    }
}
